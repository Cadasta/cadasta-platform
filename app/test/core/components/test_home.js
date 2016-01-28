import { describe, it } from 'mocha';
import React from 'react/addons';
import { expect } from 'chai';
import { shallow } from 'enzyme';

import { Home } from '../../../src/js/core/components/Home';
import RegistrationForm from '../../../src/js/account/components/RegistrationForm';


describe('Home', () => {
  it('renders registration form', () => {
    const wrapper = shallow(<Home />);
    expect(wrapper.find(RegistrationForm)).to.have.length(1);
  });
});
