import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';
import { expect } from 'chai';

import { Activate } from '../../../src/components/Account/Activate';

describe('Login', () => {
  it("invokes callback when mounted", () => {
    let tokens;
    const accountActivate = (t) => {
      tokens = t
    };

    const params = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440'
    }

    const component = TestUtils.renderIntoDocument(<Activate params={params} accountActivate={accountActivate} />);

    expect(tokens).to.deep.equal({
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440'
    });
  })
})