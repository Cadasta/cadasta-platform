import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';
import { Map } from 'immutable';

import { Profile } from '../../../src/components/Account/Profile';


describe('Profile', () => {
  it('invokes callback when the login form is submitted', () => {
    let user;
    const accountUpdate = (credentials) => {
      user = credentials
    };

    const userObj = Map({
          "username": "John",
          "email": "john@beatles.uk",
          "first_name": "John",
          "last_name": "Lennon"
        });

    const component = TestUtils.renderIntoDocument(<Profile user={userObj} accountUpdateProfile={accountUpdate} />);

    var username = component.refs.username;
    username.value = "John2";
    TestUtils.Simulate.change(username);

    var email = component.refs.email;
    email.value = "john+yoko@beatles.uk";
    TestUtils.Simulate.change(email);

    var first_name = component.refs.first_name;
    first_name.value = "John + Yoko";
    TestUtils.Simulate.change(first_name);

    var last_name = component.refs.last_name;
    last_name.value = "Lennon + Ono";
    TestUtils.Simulate.change(last_name);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(user).to.deep.equal({
      "username": "John2",
      "email": "john+yoko@beatles.uk",
      "first_name": "John + Yoko",
      "last_name": "Lennon + Ono"
    });
  });
});