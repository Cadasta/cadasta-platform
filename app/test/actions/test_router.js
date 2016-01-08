import {expect} from 'chai';
import * as actions from '../../src/actions/router';

describe('Actions: Router', () => {
  it ('creates ROUTER_REDIRECT', () => {
    const action = actions.redirect('/dashboard/');

    expect(action).to.deep.equal({
      type: actions.ROUTER_REDIRECT,
      redirectTo: '/dashboard/'
    })
  });
});
