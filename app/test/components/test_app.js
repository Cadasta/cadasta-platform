import React from 'react/addons';
import { fromJS } from 'immutable';

import { expect } from 'chai';
import { shallow } from 'enzyme';

import Message from '../../src/components/Message';
import { App } from '../../src/components/App';

describe("App", () => {
  requestsPending: 0,

  it("does not render the loading state when no requests are pending", () => {
    const messages = fromJS({
      requestsPending: 0,
      userFeedback: []
    });

    const wrapper = shallow(<App messages={messages} />);
    expect(wrapper.find('#loading')).to.have.length(0);
  });

  it("renders the loading state when requests are pending", () => {
    const messages = fromJS({
      requestsPending: 2,
      userFeedback: []
    });

    const wrapper = shallow(<App messages={messages} />);
    expect(wrapper.find('#loading')).to.have.length(1);
  });

  it("renders two messages", () => {
    const messages = fromJS({
      userFeedback: [
        {
          type: 'loading',
          msg: "Test message",
          id: 1
        }, {
          type: 'success',
          msg: "Well done",
          id: 2
        }
      ]
    });

    const user = fromJS({
      auth_token: '89usadih8sdhf'
    })

    const wrapper = shallow(<App user={user} messages={messages} />);
    expect(wrapper.find(Message)).to.have.length(2);
  });
});