import React from 'react';

const propTypes = {
  accountRegister: React.PropTypes.func.isRequired,
};

class RegistrationForm extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.accountRegister({
      username: this.refs.username.value,
      email: this.refs.email.value,
      password: this.refs.password.value,
      password_repeat: this.refs.password_repeat.value,
      first_name: this.refs.first_name.value,
      last_name: this.refs.last_name.value,
    });
  }

  render() {
    return (
      <form className="account-register form-narrow" onSubmit={this.handleFormSubmit}>

        <h1>Register for an account</h1>
        <p>By creating an account ...</p>

        <div className="form-group">
          <label htmlFor="username">Choose username</label>
          <input name="username" ref="username" type="text" className="form-control" />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input name="email" ref="email" type="email" className="form-control" />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input name="password" ref="password" type="password" className="form-control" />
        </div>

        <div className="form-group">
          <label htmlFor="password_repeat">Confirm password</label>
          <input name="password_repeat" ref="password_repeat" type="password" className="form-control" />
        </div>

        <div className="form-group">
          <label htmlFor="first_name">First name</label>
          <input name="first_name" ref="first_name" type="text" className="form-control" />
        </div>

        <div className="form-group">
          <label htmlFor="last_name">Last name</label>
          <input name="last_name" ref="last_name" type="text" className="form-control" />
        </div>

        <div className="text-center">
          <button type="submit" className="btn btn-primary btn-lg">Register</button>
        </div>

      </form>
    );
  }
}

RegistrationForm.propTypes = propTypes;

export default RegistrationForm;
