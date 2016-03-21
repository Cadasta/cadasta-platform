import TestUtils from 'react-addons-test-utils';
import React from 'react/addons';
import { expect } from 'chai';
import sinon from 'sinon';

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

    const callback = sinon.spy(accountRegister);

    const component = TestUtils.renderIntoDocument(
      <RegistrationForm accountRegister={callback} />
    );

    const username = TestUtils.findRenderedDOMComponentWithTag(component.refs.username, 'INPUT');
    username.value = 'John';
    TestUtils.Simulate.change(username);

    const email = TestUtils.findRenderedDOMComponentWithTag(component.refs.email, 'INPUT');
    email.value = 'john@beatles.uk';
    TestUtils.Simulate.change(email);

    const password = TestUtils.findRenderedDOMComponentWithTag(component.refs.password, 'INPUT');
    password.value = '123456';
    TestUtils.Simulate.change(password);

    const passwordRepeat = TestUtils.findRenderedDOMComponentWithTag(
      component.refs.password_repeat,
      'INPUT'
    );
    passwordRepeat.value = '123456';
    TestUtils.Simulate.change(passwordRepeat);

    const firstName = TestUtils.findRenderedDOMComponentWithTag(component.refs.first_name, 'INPUT');
    firstName.value = 'John';
    TestUtils.Simulate.change(firstName);

    const lastName = TestUtils.findRenderedDOMComponentWithTag(component.refs.last_name, 'INPUT');
    lastName.value = 'Lennon';
    TestUtils.Simulate.change(lastName);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(true);
  });

  it('does not invoke the callback when the form is invalid', () => {
    const callback = sinon.spy();

    const component = TestUtils.renderIntoDocument(
      <RegistrationForm accountRegister={callback} />
    );
    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(false);
  });
});
