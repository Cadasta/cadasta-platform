import { describe, it } from 'mocha';
import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';
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

    const userObj = new Map({
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    });

    const component = TestUtils.renderIntoDocument(
      <Profile user={userObj} accountUpdateProfile={accountUpdate} />
    );

    const username = component.refs.username;
    username.value = 'John2';
    TestUtils.Simulate.change(username);

    const email = component.refs.email;
    email.value = 'john+yoko@beatles.uk';
    TestUtils.Simulate.change(email);

    const firstName = component.refs.first_name;
    firstName.value = 'John + Yoko';
    TestUtils.Simulate.change(firstName);

    const lastName = component.refs.last_name;
    lastName.value = 'Lennon + Ono';
    TestUtils.Simulate.change(lastName);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);
  });
});
