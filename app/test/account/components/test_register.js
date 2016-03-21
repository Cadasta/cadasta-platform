import React from 'react/addons';
import { shallow } from 'enzyme';
import { expect } from 'chai';

import { Register } from '../../../src/js/account/components/Register';
import RegistrationForm from '../../../src/js/account/components/RegistrationForm';


describe('Account: Components: Register', () => {
  it('renders registration form', () => {
    const accountRegister = () => {};
    const wrapper = shallow(<Register accountRegister={accountRegister} />);
    expect(wrapper.find(RegistrationForm)).to.have.length(1);
  });
});
