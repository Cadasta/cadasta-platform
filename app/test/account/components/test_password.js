import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';
import sinon from 'sinon';

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
    const callback = sinon.spy(accountChangePassword);

    const component = TestUtils.renderIntoDocument(
      <Password accountChangePassword={callback} />
    );

    const newPassword = TestUtils.findRenderedDOMComponentWithTag(
      component.refs.new_password, 'INPUT');
    newPassword.value = '123456';
    TestUtils.Simulate.change(newPassword);

    const reNewPassword = TestUtils.findRenderedDOMComponentWithTag(
      component.refs.re_new_password, 'INPUT');
    reNewPassword.value = '123456';
    TestUtils.Simulate.change(reNewPassword);

    const currentPassword = TestUtils.findRenderedDOMComponentWithTag(
      component.refs.current_password, 'INPUT');
    currentPassword.value = '78910';
    TestUtils.Simulate.change(currentPassword);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(true);
  });

  it('does not invoke the callback when the form is invalid', () => {
    const callback = sinon.spy();
    const component = TestUtils.renderIntoDocument(<Password accountChangePassword={callback} />);
    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(false);
  });
});
