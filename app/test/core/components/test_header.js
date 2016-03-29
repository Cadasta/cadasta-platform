import React from 'react/addons';
import { fromJS } from 'immutable';
import { expect } from 'chai';
import mock from 'mock-require';

import { shallow } from 'enzyme';

// Mock up image require used in Header.jsx.
mock('../../../src/img/logo-white.png', { image: "logo-white.png" });

import Header from '../../../src/js/core/components/Header';

describe('Header', () => {
  it('renders login and register links when user is not logged in', () => {
    const user = fromJS({});

    const wrapper = shallow(<Header user={user} />);
    expect(wrapper.contains('Login')).to.be.true;
    expect(wrapper.contains('Register')).to.be.true;
  });

  it('renders logout and profile links when user is logged in', () => {
    const user = fromJS({ auth_token: '89usadih8sdhf' });

    const wrapper = shallow(<Header user={user} />);
    expect(wrapper.contains('Logout')).to.be.true;
    expect(wrapper.contains('Profile')).to.be.true;
  });
});
