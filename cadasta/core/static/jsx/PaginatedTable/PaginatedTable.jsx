class Head extends React.Component {
  render() {
    return <th>{this.props.label}</th>
  }
}

class Row extends React.Component {
  render() {
    return (
      <tr>
        <td>{this.props.name}</td>
        <td>{this.props.type}</td>
        <td></td>
      </tr>
    )
  }
}

class PaginatedTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      data: [],
      count: 0
    }
  }

  fetchData() {
    const url = this.props.url;
    fetch(url, {
      credentials: "same-origin",
    })
    .then(result => result.json())
    .then(data => {
      this.setState({
        data: data['results'],
        count: data['count'],
      })
    })
  }

  componentDidMount() {
    this.fetchData()
  }

  render() {
    const RowComponent = this.props.row_component;
    return (
      <table className="table table-hover">
        <thead>
          <tr>
            {this.props.columns.map(col => <Head label={col.label} />)}
            <Head />
          </tr>
        </thead>
        <tbody>
          {this.state.data.map(set => React.createElement(RowComponent, set))}
        </tbody>
      </table>
    )
  }
}
