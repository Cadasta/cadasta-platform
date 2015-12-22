import {expect} from 'chai';
import * as messageActions from '../../src/actions/messages';

describe('Actions: Messages', () => {
  it ('creates MESSAGE_DISMISS', () => {
    const action = messageActions.messageDismiss(1);

    expect(action).to.deep.equal({
      type: messageActions.MESSAGE_DISMISS,
      messageId: 1
    })
  });
});