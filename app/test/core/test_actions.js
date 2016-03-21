import * as actions from '../../src/js/core/actions';
import { expect } from 'chai';

describe('Core: Actions', () => {
  it ('creates ROUTER_REDIRECT', () => {
    const action = actions.redirect('/dashboard/');

    expect(action).to.deep.equal({
      type: actions.ROUTER_REDIRECT,
      redirectTo: '/dashboard/',
      keepMessages: true,
    });
  });
});
