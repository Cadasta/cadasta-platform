import React from 'react/addons';
import { Map } from 'immutable';
import TestUtils from 'react-addons-test-utils';

import { Logout } from '../../../src/js/account/components/Logout';


describe('Account: Components: Logout', () => {
  it('invokes accountLogout when mounted', () => {
    const user = new Map({
      auth_token: 'idsf89dsf8',
    });
    const accountLogout = sinon.spy();
    TestUtils.renderIntoDocument(<Logout user={user} accountLogout={accountLogout} />);
    expect(accountLogout.called).to.be.true;
  });
});
