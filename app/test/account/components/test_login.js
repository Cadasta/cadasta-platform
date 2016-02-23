import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';

import { Login } from '../../../src/js/account/components/Login';


describe('Account: Components: Login', () => {
  it('invokes callback when the login form is submitted', () => {
    const accountLogin = (credentials) => {
      expect(credentials).to.deep.equal({
        username: 'John',
        password: '123456',
        rememberMe: false,
      });
    };

    const callback = sinon.spy(accountLogin);

    const component = TestUtils.renderIntoDocument(<Login accountLogin={callback} />);

    const username = TestUtils.findRenderedDOMComponentWithTag(component.refs.username, 'INPUT');
    username.value = 'John';
    TestUtils.Simulate.change(username);

    const password = TestUtils.findRenderedDOMComponentWithTag(component.refs.password, 'INPUT');
    password.value = '123456';
    TestUtils.Simulate.change(password);

    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(true);
  });

  it('does not invoke the callback when the form is invalid', () => {
    const callback = sinon.spy();
    const component = TestUtils.renderIntoDocument(<Login accountLogin={callback} />);
    const forms = TestUtils.scryRenderedDOMComponentsWithTag(component, 'form');
    TestUtils.Simulate.submit(forms[0]);

    expect(callback.called).to.equal(false);
  });
});
