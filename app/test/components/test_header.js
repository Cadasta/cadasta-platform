import React from 'react/addons';
import { fromJS } from 'immutable';

import { expect } from 'chai';
import { shallow } from 'enzyme';

import Header from '../../src/components/Header';

describe("Header", () => {
  it("renders login and register links when user is not logged in", () => {
    const user = fromJS({});

    const wrapper = shallow(<Header user={user} />);
    expect(wrapper.contains("Login")).to.be.true;
    expect(wrapper.contains("Register")).to.be.true;
  });

  it("renders logout and profile links when user is logged in", () => {
    const user = fromJS({ auth_token: '89usadih8sdhf' });

    const wrapper = shallow(<Header user={user} />);
    expect(wrapper.contains("Logout")).to.be.true;
    expect(wrapper.contains("Profile")).to.be.true;
  });
});