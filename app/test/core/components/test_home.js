import React from 'react/addons';
import { shallow } from 'enzyme';
import { expect } from 'chai';

import { Home } from '../../../src/js/core/components/Home';
import RegistrationForm from '../../../src/js/account/components/RegistrationForm';


describe('Home', () => {
  it('renders registration form', () => {
    const accountRegister = () => {};
    const wrapper = shallow(<Home accountRegister={accountRegister} />);
    expect(wrapper.find(RegistrationForm)).to.have.length(1);
  });
});
