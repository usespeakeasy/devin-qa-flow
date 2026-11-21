#!/usr/bin/env python3
"""Provision isolated develop organization fixtures through normal Partners APIs.

No E2E-user endpoint or mobile-device signup is needed. Journal paths must be
private and outside git. A pending POST requires operator reconciliation, never
an automatic retry (the API has no idempotency keys).
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.parse
import uuid

import qa_org as q


def persist(path, state):
    tmp = Path(str(path) + '.tmp')
    with open(tmp, 'w', opener=lambda p, f: os.open(p, f, 0o600)) as out:
        json.dump(state, out, indent=2)
    os.replace(tmp, path)


def mutation(path, state, key, endpoint, body, method='POST'):
    if key in state:
        return state[key]
    if state.get('pending'):
        raise RuntimeError('Reconcile pending backend mutation before resuming: ' + state['pending'])
    state['pending'] = key
    persist(path, state)
    value = q.request(endpoint, method, body)
    state[key] = value
    del state['pending']
    persist(path, state)
    return value


def provision(path, holder, product, language_pair):
    if path.exists():
        state = json.loads(path.read_text())
        if state['holder'] != holder or state['product'] != product or state['language_pair'] != language_pair:
            raise ValueError('Resume must use the original holder, product and language pair')
    else:
        nonce = uuid.uuid4().hex
        provenance = dict(source=q.SOURCE, created_by=holder,
                          created_at=dt.datetime.now(dt.timezone.utc).isoformat(), nonce=nonce)
        now = dt.datetime.now(dt.timezone.utc)
        state = dict(holder=holder, product=product, language_pair=language_pair,
                     provenance=provenance, fingerprint=q.fingerprint(provenance),
                     name='Devin QA required-assessment ' + nonce[:10],
                     email='devin+qa-org-' + nonce + '@usespeak.com',
                     start=(now-dt.timedelta(days=5)).isoformat(),
                     end=(now+dt.timedelta(days=5)).isoformat(),
                     term_end=(now+dt.timedelta(days=30)).isoformat())
        q.save(path, state)
    mutation(path, state, 'organization_created', '/v1/partners/admin/organizations/', dict(
        name=state['name'], description=json.dumps(dict(provenance=state['provenance'], fingerprint=state['fingerprint'])),
        disableSaveStreak=False, regionCodes=['US'], parentOrganizationIds=[], childOrganizationIds=[],
        enableB2BExperience=True, enableStandaloneAssessments=True, enableOnboarding=False,
        enableOnboardingCioCampaigns=False, timezone='America/Los_Angeles'))
    if 'org' not in state:
        found = q.request('/v1/partners/admin/organizations/?name=' + urllib.parse.quote(state['name']))['organizations']
        found = [o for o in found if o['name'] == state['name'] and state['fingerprint'] in (o.get('description') or '')]
        if len(found) != 1:
            raise RuntimeError('Expected exactly one fingerprinted organization; reconcile journal')
        state['org'] = found[0]['id']; persist(path, state)
    org = state['org']
    # Re-prove ownership on every resume before changing remote state.
    remote = q.request('/v1/partners/admin/organizations/' + org)['organization']
    if state['fingerprint'] not in (remote.get('description') or ''):
        raise RuntimeError('Organization provenance mismatch')
    mutation(path, state, 'subscription_created', '/v1/partners/admin/organization-subscriptions/', dict(
        businessCustomerId=state['name'], description='Dedicated dev-only QA fixture',
        termStartAt=state['start'], termEndAt=state['term_end'], capacity=1, allowOverage=False,
        organizationId=org, speakProductId=product, trial=True, revenueGenerating=False, createHubspotDeal=False))
    if 'subscription' not in state:
        subscriptions = q.request(f'/v1/partners/organizations/{org}/subscriptions')['data']
        if len(subscriptions) != 1:
            raise RuntimeError('Expected one subscription; reconcile journal')
        state['subscription'] = subscriptions[0]['id']; persist(path, state)
    mutation(path, state, 'learner_created', f'/v1/partners/admin/organizations/{org}/users', dict(
        user=dict(name='Devin QA Organization Learner', email=state['email'], selectedLanguagePairId=language_pair)))
    state['learner'] = state['learner_created']['organizationUser']['userId']; persist(path, state)
    mutation(path, state, 'seat_assigned', '/v1/partners/admin/organization-subscription-assignments/', dict(
        organizationSubscriptionId=state['subscription'],
        user=dict(name='Devin QA Organization Learner', email=state['email'], selectedLanguagePairId=language_pair)))
    config = q.request(f'/v1/partners/organizations/{org}/assessment')
    if not config['canRequireAppAssessment']:
        raise RuntimeError('Provisioned org/learner/seat; required-assessment rollout is OFF for this organization. '
                           'Enable app_assessments_required targeting this organization, then resume the same journal. '
                           'No fixture registered or marked ready.')
    mutation(path, state, 'recurring_disabled', f'/v1/partners/organizations/{org}/assessment', dict(isActive=False), 'PATCH')
    if state.get('schedule_id'):
        # Operator-reconciled journals may already have a non-required schedule.
        mutation(path, state, 'schedule',
                 f'/v1/partners/organizations/{org}/scheduled-assessments/{state["schedule_id"]}',
                 dict(requireAppAssessment=True), 'PATCH')
    else:
        mutation(path, state, 'schedule', f'/v1/partners/organizations/{org}/scheduled-assessments', dict(
            name=state['name'], startAt=state['start'], endAt=state['end'],
            requireAppAssessment=True, audience=dict(userIds=[state['learner']])))
    if not state['schedule'].get('requireAppAssessment'):
        raise RuntimeError('Backend did not save the required schedule; do not register')
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--holder', required=True)
    parser.add_argument('--product', required=True, help='Existing develop SpeakProduct ID (no payment is created)')
    parser.add_argument('--language-pair', default='korean-english')
    args = parser.parse_args()
    state = provision(args.journal, args.holder, args.product, args.language_pair)
    print(json.dumps(dict(organization_id=state['org'], learner_user_id=state['learner'],
                         fingerprint=state['fingerprint'], status='provisioned_not_registered')))
    print('Before register: verify learner-authenticated eligibility/required state and make the baseline manifest.')


if __name__ == '__main__':
    main()
