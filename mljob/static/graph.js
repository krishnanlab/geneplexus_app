$( document ).ready(function() {
  graph_aspect_ratio = 2
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
  console.log(dataset);
  console.log(allNodes);
  //var width = 1080;
  //var height = 600;
  var width = $('.result_container').width() * (8/12);
  console.log(width);
  var height = width / graph_aspect_ratio;
  console.log(height);


  const svg = d3.select('svg');
  /*const svg = d3.select('#graph_area')
    .append('svg')
    .attr('width', width)
    .attr('height', height);*/
  const g = svg.append('g');

  $('#edge_slider').slider({
    range: true,
    min: 0.00,
    max: 1.00,
    values: [0.00, 1.00],
    step: 0.01,
    slide: function( event, ui ) {
      console.log(ui.values);
      $('#edge_lower').val(ui.values[0].toFixed(2));
      $('#edge_upper').val(ui.values[1].toFixed(2));
    }
  });
  $('#node_slider').slider();

  const forceProperties = {
    charge: {
      strength: -1000,
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
  const linkElements = g
          .attr("class", "links")
          .selectAll("line")
          .data(dataset.links)
          .enter().append("line")
          .style("stroke", "#ADA9A8")
          .style("stroke-width", function(d) { return (d.weight); });

  //const nodeElements = svg.append('g')
  const nodeElements = g
    .selectAll('circle')
    .data(allNodes)
    .enter()
    .append('circle')
    .attr('r', function(d){return nodescale(d.Probability)})
    .attr('fill', function(d){return myColor(d.Class) })
    .call(d3.drag()
            .on("start", onDragStarted)
            .on("drag", onDrag)
            .on("end", onDragEnded));
  zoom_handler = d3.zoom().on('zoom', onZoomAction);
  zoom_handler(svg);

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
      g.attr("transform", d3.event.transform)
  }

  function onDragStarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function onDrag(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
  }

  function onDragEnded(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
});