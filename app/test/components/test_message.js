import React from 'react/addons';
import { Map } from 'immutable';

import { expect } from 'chai';
import { shallow } from 'enzyme';
import sinon from 'sinon';

import Message from '../../src/components/Message';


describe("Message", () => {
  it("fully renders the component", () => {
    const message = Map({
      type: 'loading',
      msg: "Test message",
      id: 1,
      dismissable: true
    });

    const callback = () => {}

    const wrapper = shallow(<Message message={message} onDismiss={callback} />);
    expect(wrapper.find('p')).to.have.length(1);
    expect(wrapper.find('p').text()).to.equal("Test message");
    expect(wrapper.find('button')).to.have.length(1);
  });

  it("does not render the dismiss button when message is not dismissable", () => {
    const message = Map({
      type: 'loading',
      msg: "Test message",
      id: 1,
      dismissable: false
    });

    const callback = () => {}

    const wrapper = shallow(<Message message={message} />);
    expect(wrapper.find('p')).to.have.length(1);
    expect(wrapper.find('p').text()).to.equal("Test message");
    expect(wrapper.find('button')).to.have.length(0);
  });

  it("invokes the callback when dismiss button is clicked", () => {
    const message = Map({
      type: 'loading',
      msg: "Test message",
      id: 1,
      dismissable: true
    });

    const callback = sinon.spy();

    const wrapper = shallow(<Message message={message} messageDismiss={callback} />);    
    wrapper.find('button').simulate('click');
    expect(callback.calledOnce).to.be.true;
  });
});