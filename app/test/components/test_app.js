import React from 'react/addons';
import { fromJS } from 'immutable';

import { expect } from 'chai';
import { shallow } from 'enzyme';

import Message from '../../src/components/Message';
import { App } from '../../src/components/App';

describe("App", () => {
  it("renders two messages", () => {
    const messages = fromJS([
      {
        type: 'loading',
        msg: "Test message",
        id: 1
      }, {
        type: 'success',
        msg: "Well done",
        id: 2
      }
    ]);

    const wrapper = shallow(<App messages={messages} />);
    expect(wrapper.find(Message)).to.have.length(2);
  });
});