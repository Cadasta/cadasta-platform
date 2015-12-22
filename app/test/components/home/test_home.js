import { Map } from 'immutable';

import React from 'react/addons';
import { expect } from 'chai';
import { shallow } from 'enzyme';

import { Home } from '../../../src/components/home';
import SplashPage from '../../../src/components/home/SplashPage';
import Dashboard from '../../../src/components/home/Dashboard';


describe('Home', () => {
  it('renders the login form when no user object is provided', () => {
    const userObj = Map({ });
    const wrapper = shallow(<Home user={userObj} />);
    expect(wrapper.find(SplashPage)).to.have.length(1);
  });

  it('renders the Dashboard when a user object is provided', () => {
    const userObj = Map({
      username: "john",
      email: "john@beatles.uk",
      first_name: "John",
      last_name: "Lennon",
      auth_token: "idsf89dsf8"
    });

    const wrapper = shallow(<Home user={userObj} />);
    expect(wrapper.find(Dashboard)).to.have.length(1);
  });
});