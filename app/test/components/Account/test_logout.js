import React from 'react/addons';
import { Map } from 'immutable';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';
import sinon from 'sinon';

import { Logout } from '../../../src/components/Account/Logout';


describe('Logout', () => {
  it('invokes accountLogout when mounted', () => {
    const user = Map({
      auth_token: "idsf89dsf8"
    });
    const accountLogout = sinon.spy();
    const component = TestUtils.renderIntoDocument(<Logout user={user} accountLogout={accountLogout} />);
    expect(accountLogout.called).to.be.true;
  });
});