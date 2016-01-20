import { describe, it } from 'mocha';
import React from 'react/addons';
import { expect } from 'chai';
import { shallow } from 'enzyme';

import { Register } from '../../../src/js/account/components/Register';
import RegistrationForm from '../../../src/js/account/components/RegistrationForm';


describe('Account: Components: Register', () => {
  it('renders registration form', () => {
    const wrapper = shallow(<Register />);
    expect(wrapper.find(RegistrationForm)).to.have.length(1);
  });
});
