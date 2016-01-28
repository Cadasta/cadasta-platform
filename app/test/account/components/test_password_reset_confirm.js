import { describe, it } from 'mocha';
import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { PasswordResetConfirm } from '../../../src/js/account/components/PasswordResetConfirm';

describe('Account: Components: PasswordResetConfirm', () => {
  it('invokes callback when the reset password confirmation from is submitted', () => {
    const accountResetConfirmPassword = (passwords) => {
      expect(passwords).to.deep.equal({
        new_password: '123456',
        re_new_password: '123456',
        uid: 'MQ',
        token: '489-963055ee7742ad6c4440',
      });
    };

    const params = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    };

    const component = TestUtils.renderIntoDocument(
      <PasswordResetConfirm
        params={params}
        accountResetConfirmPassword={accountResetConfirmPassword}
      />
    );

    const newPassword = component.refs.new_password;
    newPassword.value = '123456';
    TestUtils.Simulate.change(newPassword);

    const reNewPassword = component.refs.re_new_password;
    reNewPassword.value = '123456';
    TestUtils.Simulate.change(reNewPassword);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);
  });
});
