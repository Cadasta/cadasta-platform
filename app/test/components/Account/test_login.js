import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { Login } from '../../../src/components/Account/Login';


describe('Login', () => {
  it('invokes callback when the login form is submitted', () => {
    let user;
    const accountLogin = (credentials) => {
      user = credentials
    };

    const component = TestUtils.renderIntoDocument(<Login accountLogin={accountLogin} />);

    var username = component.refs.username;
    username.value = "John";
    TestUtils.Simulate.change(username);

    var password = component.refs.password;
    password.value = "123456";
    TestUtils.Simulate.change(password);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(user).to.deep.equal({
      "username": "John",
      "password": "123456"
    });
  });
});