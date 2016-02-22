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

    const callback = sinon.spy(accountResetPassword);

    const component = TestUtils.renderIntoDocument(
      <PasswordReset accountResetPassword={callback} />
    );

    const email = TestUtils.findRenderedDOMComponentWithTag(component.refs.email, 'INPUT');
    email.value = 'john@beatles.uk';
    TestUtils.Simulate.change(email);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(true);
  });

  it('does not invoke the callback when the form is invalid', () => {
    const callback = sinon.spy();
    const component = TestUtils.renderIntoDocument(
      <PasswordReset accountResetPassword={callback} />
    );
    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(false);
  });
});
