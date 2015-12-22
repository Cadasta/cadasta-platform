import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import SplashPage from '../../../src/components/home/SplashPage';


describe('SplashPage', () => {
  it('invokes callback when the login form is submitted', () => {
    let user;
    const accountLogin = (credentials) => user = credentials;

    const component = TestUtils.renderIntoDocument(<SplashPage accountLogin={accountLogin} />);

    var username = component.refs.username;
    username.value = "John";
    TestUtils.Simulate.change(username);

    var password = component.refs.password;
    password.value = "123456";
    TestUtils.Simulate.change(password);

    const buttons = TestUtils.scryRenderedDOMComponentsWithTag(component, 'button');
    TestUtils.Simulate.click(buttons[0]);

    expect(user).to.deep.equal({
      "username": "John",
      "password": "123456"
    });
  });
});