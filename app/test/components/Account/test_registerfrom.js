import TestUtils from 'react-addons-test-utils';
import React from 'react/addons';
import { expect } from 'chai';

import RegistrationForm from '../../../src/components/Account/RegistrationForm';

describe('RegistrationForm', () => {
  it('invokes callback when the register form is submitted', () => {
    let user;
    const accountRegister = (credentials) => {
      user = credentials
    };

    const component = TestUtils.renderIntoDocument(<RegistrationForm accountRegister={accountRegister} />);

    var username = component.refs.username;
    username.value = "John";
    TestUtils.Simulate.change(username);

    var email = component.refs.email;
    email.value = "john@beatles.uk";
    TestUtils.Simulate.change(email);

    var password = component.refs.password;
    password.value = "123456";
    TestUtils.Simulate.change(password);

    var password_repeat = component.refs.password_repeat;
    password_repeat.value = "123456";
    TestUtils.Simulate.change(password_repeat);

    var first_name = component.refs.first_name;
    first_name.value = "John";
    TestUtils.Simulate.change(first_name);

    var last_name = component.refs.last_name;
    last_name.value = "Lennon";
    TestUtils.Simulate.change(last_name);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(user).to.deep.equal({
      "username": "John",
      "password": "123456",
      "password_repeat": "123456",
      "email": "john@beatles.uk",
      "first_name": "John",
      "last_name": "Lennon"
    });
  });
});