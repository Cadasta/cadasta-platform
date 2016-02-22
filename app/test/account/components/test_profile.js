import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { Map } from 'immutable';

import { Profile } from '../../../src/js/account/components/Profile';


describe('Account: Components: Profile', () => {
  it('invokes callback when the login form is submitted', () => {
    const accountUpdate = (credentials) => {
      expect(credentials).to.deep.equal({
        username: 'John2',
        email: 'john+yoko@beatles.uk',
        first_name: 'John + Yoko',
        last_name: 'Lennon + Ono',
      });
    };

    const callback = sinon.spy(accountUpdate);

    const userObj = new Map({
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    });

    const component = TestUtils.renderIntoDocument(
      <Profile user={userObj} accountUpdateProfile={callback} />
    );

    const username = TestUtils.findRenderedDOMComponentWithTag(component.refs.username, 'INPUT');
    username.value = 'John2';
    TestUtils.Simulate.change(username);

    const email = TestUtils.findRenderedDOMComponentWithTag(component.refs.email, 'INPUT');
    email.value = 'john+yoko@beatles.uk';
    TestUtils.Simulate.change(email);

    const firstName = TestUtils.findRenderedDOMComponentWithTag(component.refs.first_name, 'INPUT');
    firstName.value = 'John + Yoko';
    TestUtils.Simulate.change(firstName);

    const lastName = TestUtils.findRenderedDOMComponentWithTag(component.refs.last_name, 'INPUT');
    lastName.value = 'Lennon + Ono';
    TestUtils.Simulate.change(lastName);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(true);
  });

  it('does not invoke the callback when the form is invalid', () => {
    const callback = sinon.spy();

    const userObj = new Map({
      username: '',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    });

    const component = TestUtils.renderIntoDocument(
      <Profile user={userObj} accountUpdateProfile={callback} />
    );
    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(false);
  });
});
