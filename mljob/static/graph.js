$( document ).ready(function() {
  graph_aspect_ratio = 2;
  $('body').on('click', '#graph_tab', function() {
    
    var width = $('.result_container').width() * (8/12);
    console.log(width);
    var height = width / graph_aspect_ratio;
    console.log(height);
    svg
      .attr('width', width)
      .attr('height', height);
  });

  var allNodes = dataset.nodes.sort((a, b) => (a.Probability - b.Probability))
  //var width = 1080;
  //var height = 600;
  var width = $('.result_container').width() * (8/12);
  console.log(width);
  var height = width / graph_aspect_ratio;
  console.log(height);
  selectedNode = null;

  const svg = d3.select('svg');
  /*const svg = d3.select('#graph_area')
    .append('svg')
    .attr('width', width)
    .attr('height', height);*/
  //const g = svg.append('g');

  $('#node_slider').slider({
    range: true,
    min: 0.00,
    max: 1.00,
    values: [0.00, 1.00],
    step: 0.01,
    slide: function( event, ui ) {
      $('#node_lower').val(ui.values[0].toFixed(2));
      $('#node_upper').val(ui.values[1].toFixed(2));
      modifyNodeCount(ui.values[0], ui.values[1]);
    }
  });

  const forceProperties = {
    charge: {
      strength: -100,
    },
    collide: {
      strength: 0.3,
      radius: 5,
    },

  }
  const simulation = d3.forceSimulation()
    .force('link', d3.forceLink())
    .force('charge', d3.forceManyBody()) 
    .force('collide', d3.forceCollide())
    .force('center', d3.forceCenter(width / 2, height / 2))

  var nodescale = d3.scaleLinear().domain([0, .3]).range([1, 5])

  var data = ['P','U','N']
  var myColor = d3.scaleOrdinal().domain(data)
      .range(["#00ccbc","#6598bf","#CC333F"])



  //const linkElements = svg.append("g")
  linkElements = svg.append('g')
          .attr("class", "links")
          .selectAll("line")
          .data(dataset.links)
          .enter().append("line")
          .style("stroke", "#ADA9A8")
          .style("stroke-width", function(d) { return (d.weight); });

  //const nodeElements = svg.append('g')
  nodeElements = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('circle')
    .data(allNodes)
    .enter()
    .append('circle')
    .attr('r', function(d){return nodescale(d.Probability)})
    .attr('fill', function(d){return myColor(d.Class) })
    .classed('node', true)
    .classed("fixed", d => d.fx !== undefined)
    .call(d3.drag()
            .on("start", onDragStarted)
            .on("drag", onDrag)
            .on("end", onDragEnded))
    .on('click', onClick);
  
  zoom_handler = d3.zoom().on('zoom', onZoomAction);
  zoom_handler(svg);

  d3.selectAll('circle').append("text")
        .attr("text-anchor", "middle")
        .text(function(d) { return d.Symbol; })
        .attr('alignment-baseline', 'middle')
        .style('color', 'black');

  simulation.nodes(allNodes).on('tick', onTick);

  simulation.force('charge')
    .strength(forceProperties.charge.strength);
  simulation.force('collide')
    .strength(forceProperties.collide.strength)
    .radius(forceProperties.collide.radius);
  simulation.force('link')
      .id(function(d) {return d.id})
      .links(dataset.links);
  function onTick() {
    nodeElements
      .attr('cx', node => node.x)
      .attr('cy', node => node.y)
    
    linkElements
      .attr('x1', link => link.source.x)
      .attr('y1', link => link.source.y)
      .attr('x2', link => link.target.x)
      .attr('y2', link => link.target.y)
  }

  function onZoomAction(){
    d3.selectAll('g.nodes').attr("transform", d3.event.transform)
    d3.selectAll('g.links').attr("transform", d3.event.transform)
    //g.attr("transform", d3.event.transform)
  }

  function onDragStarted(d) {
    d3.select(this).classed("fixed", true);
  }

  function onDrag(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
    simulation.alpha(1).restart();
  }

  function onDragEnded(d) {
  }

  function onClick(d) {
    delete d.fx;
    delete d.fy;
    d3.select(selectedNode).style('stroke', 'transparent');
    setSidebarInformation(d);
    d3.select(this).classed("fixed", false);
    d3.select(this).style('stroke', 'red');
    selectedNode = this;
    simulation.alpha(1).restart();
  }

  function setSidebarInformation(d) {
    $('#static_id').text(d.id);
    $('#static_class').text(d.Class);
    $('#static_known').text(d['Known/Novel'])
    $('#static_name').text(d.Name);
    $('#static_prob').text(d.Probability);
    $('#static_rank').text(d.Rank);
    $('#static_symbol').text(d.Symbol);
    $('#static_site').attr('href', 'https://www.ncbi.nlm.nih.gov/gene/' + d.id, '_blank');
    $('#static_site').text('Click here');
  }

  function modifyNodeCount(startThresh, endThresh) {
    d3.selectAll('g.nodes').remove();
    d3.selectAll('g.links').remove();
    //allNodes = dataset.nodes.sort((a, b) => (a.Probability - b.Probability))
    newNodes = dataset.nodes.filter(
      function(n) {
        if (n.Probability >= startThresh && n.Probability <= endThresh) {
          return true;
        }
        return false;
      }
    )
    newLinks = dataset.links.filter(
      function(l) {
          for(let i = 0; i < newNodes.length; i++){
              if (l.source.id == newNodes[i].id || l.target.id == newNodes[i].id) {
                  return true;
              }
          }
          return false;
      }
  )
  console.log(newNodes);
  console.log(newLinks);
    linkElements = svg.append('g')
        .attr("class", "links")
        .selectAll("line")
        .data(newLinks)
        .enter().append("line")
        .style("stroke", "#ADA9A8")
        .style("stroke-width", function(d) { return (d.weight); });
    nodeElements = svg.append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(newNodes)
      .enter()
      .append('circle')
      .attr('r', function(d){return nodescale(d.Probability)})
      .attr('fill', function(d){return myColor(d.Class) })
      .classed('node', true)
      .classed("fixed", d => d.fx !== undefined)
      .call(d3.drag()
              .on("start", onDragStarted)
              .on("drag", onDrag)
              .on("end", onDragEnded))
      .on('click', onClick);
    zoom_handler = d3.zoom().on('zoom', onZoomAction);
    zoom_handler(svg);
    nodeElements.append("text")
        .attr("text-anchor", "middle")
        .text(function(d) { return d.Symbol; })
        .attr('alignment-baseline', 'middle');
    simulation.alpha(1).restart();
  }
});