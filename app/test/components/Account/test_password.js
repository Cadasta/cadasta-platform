import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { Password } from '../../../src/components/Account/Password';


describe('Password', () => {
  it("invokes callback when the change password from is submitted", () => {
    let passwords;
    const accountChangePassword = (p) => {
      passwords = p
    };

    const component = TestUtils.renderIntoDocument(<Password accountChangePassword={accountChangePassword} />);

    let new_password = component.refs.new_password;
    new_password.value = "123456";
    TestUtils.Simulate.change(new_password);

    let re_new_password = component.refs.re_new_password;
    re_new_password.value = "123456";
    TestUtils.Simulate.change(re_new_password);

    let current_password = component.refs.current_password;
    current_password.value = "78910";
    TestUtils.Simulate.change(current_password);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(passwords).to.deep.equal({
      "new_password": "123456",
      "re_new_password": "123456",
      "current_password": "78910"
    });
  });
});