import { describe, it } from 'mocha';
import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { Login } from '../../../src/js/account/components/Login';


describe('Account: Components: Login', () => {
  it('invokes callback when the login form is submitted', () => {
    const accountLogin = (credentials) => {
      expect(credentials).to.deep.equal({
        username: 'John',
        password: '123456',
        rememberMe: false,
      });
    };

    const component = TestUtils.renderIntoDocument(<Login accountLogin={accountLogin} />);

    const username = component.refs.username;
    username.value = 'John';
    TestUtils.Simulate.change(username);

    const password = component.refs.password;
    password.value = '123456';
    TestUtils.Simulate.change(password);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);
  });
});
