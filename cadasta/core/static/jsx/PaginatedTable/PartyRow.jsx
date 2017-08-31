class PartyRow extends React.Component {
  render() {
    return (
      <tr>
        <td>{this.props.name}</td>
        <td>{this.props.type}</td>
        <td></td>
      </tr>
    );
  }
}
