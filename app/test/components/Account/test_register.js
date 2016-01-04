import React from 'react/addons';
import { expect } from 'chai';
import { shallow } from 'enzyme';

import { Register } from '../../../src/components/Account/Register';
import RegistrationForm from '../../../src/components/Account/RegistrationForm';


describe('Home', () => {
  it('renders registration form', () => {
    const wrapper = shallow(<Register />);
    expect(wrapper.find(RegistrationForm)).to.have.length(1);
  });
});