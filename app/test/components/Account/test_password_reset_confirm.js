import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { PasswordResetConfirm } from '../../../src/components/Account/PasswordResetConfirm';

describe('PasswordReset', () => {
  it("invokes callback when the reset password confirmation from is submitted", () => {
    let passwords;
    const accountResetConfirmPassword = (p) => {
      passwords = p
    };

    const params = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440'
    }

    const component = TestUtils.renderIntoDocument(<PasswordResetConfirm params={params} accountResetConfirmPassword={accountResetConfirmPassword} />);

    let new_password = component.refs.new_password;
    new_password.value = "123456";
    TestUtils.Simulate.change(new_password);

    let re_new_password = component.refs.re_new_password;
    re_new_password.value = "123456";
    TestUtils.Simulate.change(re_new_password);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(passwords).to.deep.equal({
      "new_password": "123456",
      "re_new_password": "123456",
      "uid": "MQ",
      "token": "489-963055ee7742ad6c4440"
    });
  })
});