import React from 'react/addons';
import { expect } from 'chai';
import { shallow } from 'enzyme';

import { Home } from '../../../src/components/Home';
import RegistrationForm from '../../../src/components/Account/RegistrationForm';


describe('Home', () => {
  it('renders registration form', () => {
    const wrapper = shallow(<Home />);
    expect(wrapper.find(RegistrationForm)).to.have.length(1);
  });
});