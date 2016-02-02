import TestUtils from 'react-addons-test-utils';
import React from 'react/addons';

import RegistrationForm from '../../../src/js/account/components/RegistrationForm';

describe('Account: Components: RegistrationForm', () => {
  it('invokes callback when the register form is submitted', () => {
    const accountRegister = (credentials) => {
      expect(credentials).to.deep.equal({
        username: 'John',
        password: '123456',
        password_repeat: '123456',
        email: 'john@beatles.uk',
        first_name: 'John',
        last_name: 'Lennon',
      });
    };

    const component = TestUtils.renderIntoDocument(
      <RegistrationForm accountRegister={accountRegister} />
    );

    const username = component.refs.username;
    username.value = 'John';
    TestUtils.Simulate.change(username);

    const email = component.refs.email;
    email.value = 'john@beatles.uk';
    TestUtils.Simulate.change(email);

    const password = component.refs.password;
    password.value = '123456';
    TestUtils.Simulate.change(password);

    const passwordRepeat = component.refs.password_repeat;
    passwordRepeat.value = '123456';
    TestUtils.Simulate.change(passwordRepeat);

    const firstName = component.refs.first_name;
    firstName.value = 'John';
    TestUtils.Simulate.change(firstName);

    const lastName = component.refs.last_name;
    lastName.value = 'Lennon';
    TestUtils.Simulate.change(lastName);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);
  });
});
