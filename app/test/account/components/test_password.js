import { describe, it } from 'mocha';
import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { Password } from '../../../src/js/account/components/Password';


describe('Account: Components: Password', () => {
  it('invokes callback when the change password form is submitted', () => {
    const accountChangePassword = (passwords) => {
      expect(passwords).to.deep.equal({
        new_password: '123456',
        re_new_password: '123456',
        current_password: '78910',
      });
    };

    const component = TestUtils.renderIntoDocument(
      <Password accountChangePassword={accountChangePassword} />
    );

    const newPassword = component.refs.new_password;
    newPassword.value = '123456';
    TestUtils.Simulate.change(newPassword);

    const reNewPassword = component.refs.re_new_password;
    reNewPassword.value = '123456';
    TestUtils.Simulate.change(reNewPassword);

    const currentPassword = component.refs.current_password;
    currentPassword.value = '78910';
    TestUtils.Simulate.change(currentPassword);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);
  });
});
