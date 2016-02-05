import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';

import { PasswordReset } from '../../../src/js/account/components/PasswordReset';

describe('Account: Components: PasswordReset', () => {
  it('invokes callback when the reset password form is submitted', () => {
    const accountResetPassword = (user) => {
      expect(user).to.deep.equal({
        email: 'john@beatles.uk',
      });
    };

    const component = TestUtils.renderIntoDocument(
      <PasswordReset accountResetPassword={accountResetPassword} />
    );

    const email = component.refs.email;
    email.value = 'john@beatles.uk';
    TestUtils.Simulate.change(email);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);
  });
});
