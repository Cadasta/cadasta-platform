import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { PasswordReset } from '../../../src/components/Account/PasswordReset';

describe('PasswordReset', () => {
  it("invokes callback when the reset password from is submitted", () => {
    let user;
    const accountResetPassword = (u) => {
      user = u
    };

    const component = TestUtils.renderIntoDocument(<PasswordReset accountResetPassword={accountResetPassword} />);

    let email = component.refs.email;
    email.value = "john@beatles.uk";
    TestUtils.Simulate.change(email);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(user).to.deep.equal({
      "email": "john@beatles.uk"
    });
  });
});