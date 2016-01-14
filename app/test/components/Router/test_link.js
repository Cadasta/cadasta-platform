import React from 'react/addons';
import { expect } from 'chai';
import { mount } from 'enzyme';

import Link from '../../../src/components/Router/Link';
import { Link as RLink } from 'react-router';

import { dismissMessages } from '../../../src/actions/messages';

import configureMockStore from 'redux-mock-store'
import thunk from 'redux-thunk'

var mockStore = configureMockStore([ thunk ]);


describe('Link', () => {
  it('renders using react-router link', () => {
    const wrapper = mount(<Link to={'/dashboard/'}>Link Text</Link>);
    expect(wrapper.find(RLink)).to.have.length(1);

    const routerLink = wrapper.find(RLink);
    expect(routerLink.props().to).to.equal('/dashboard/');
    expect(routerLink.text()).to.contain("Link Text");
  });

  it('dispatches dismissMessages on click', (done) => {
    const expectedActions = [ dismissMessages() ]

    const store = mockStore({}, expectedActions, done);
    const context = { store };

    const wrapper = mount(<Link to={'/dashboard/'}>Link Text</Link>, { context });
    wrapper.simulate('click');
  });
});