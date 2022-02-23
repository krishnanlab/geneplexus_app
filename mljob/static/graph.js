$( document ).ready(function() {
  graph_aspect_ratio = 2;
  r = 0;
  $('body').on('click', '#graph_tab', function() {
    
    var width = $('.result_container').width() * (8/12);
    var height = width / graph_aspect_ratio;
    r = -parseInt(Math.min(width, height) / 4)
    svg
      .attr('width', width)
      .attr('height', height);
  });
  var api_endpoint = 'http://mygene.info/v3/query/q=entrezgene:'
  var allNodes = dataset.nodes.sort((a, b) => (a.Probability - b.Probability))
  var width = $('.result_container').width() * (8/12);
  var height = width / graph_aspect_ratio;
  selectedNode = null;
  selectedEdges = [];

  const svg = d3.select('svg');
  const g = svg.append('g');

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
      strength: -75,
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
    .force("forceX", d3.forceX(width/2).strength(.05) )
    .force("forceY", d3.forceY(height/2).strength(.05) );

  var nodescale = d3.scaleLinear().domain([0, .3]).range([1, 5])

  var data = ['P','U','N']
  var myColor = d3.scaleOrdinal().domain(data)
      .range(["#00ccbc","#6598bf","#CC333F"])

  linkElements = g.append('g')
          .attr("class", "links")
          .selectAll("line")
          .data(dataset.links)
          .enter().append("line")
          .style("stroke", "#ADA9A8")
          .style("stroke-width", function(d) { return (d.weight); });

    nodeElements = g.append('g')
    .attr('class', 'nodes')
    .selectAll('circle')
    .data(allNodes)
    .enter()
    .append('g')
    .attr('class', 'nodeHolder');

    nodeElements
    .append('circle')
    .attr('r', function(d){return nodescale(d.Probability)})
    .attr('fill', function(d){return myColor(d.Class) })
    .classed('node', true)
    .classed("fixed", d => d.fx !== undefined);
  
  zoom_handler = d3.zoom().on('zoom', onZoomAction);
  zoom_handler(svg);
  svg.call(zoom_handler.transform, d3.zoomIdentity.scale(0.8));

  nodeElements.append("text")
  .attr("text-anchor", "middle")
  .text(function(d) { return d.Symbol; })
  .attr('alignment-baseline', 'middle')
  .style("font-size", "50%");
  
  nodeElements.call(d3.drag()
  .on("start", onDragStarted)
  .on("drag", onDrag)
  .on("end", onDragEnded))
  .on('click', onClick);

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
      .attr("transform", function(d) {
        return "translate(" + d.x + "," + d.y + ")";
      })
    
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
    d3.select(this).classed("fixed", true);
  }

  function onDrag(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
    simulation.alpha(0.1).restart();
  }

  function onDragEnded(d) {
    simulation.alpha(1).restart();
  }

  function onClick(d) {
    delete d.fx;
    delete d.fy;
    theCircle = d3.select(this).select('circle');
    if (selectedNode != null) {
      selectedNode.style('stroke', 'transparent');
    }
    setSidebarInformation(d);
    theCircle.classed("fixed", false);
    theCircle.style('stroke', 'red');
    selectedNode = theCircle;
    simulation.alpha(.01).restart();
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
    $.ajax({
      method: 'GET',
      url: 'https://mygene.info/v3/gene/' + d.id,
      success: function(result, status, xhr) {
        console.log(result);
      },
      complete: function(xhr, status) {

      }
    })
  }

  function modifyNodeCount(startThresh, endThresh) {
    d3.selectAll('g.nodes').remove();
    d3.selectAll('g.links').remove();
    //allNodes = dataset.nodes.sort((a, b) => (a.Probability - b.Probability))
    newNodes = []
    oldNodes = []
    for (let i = 0; i < dataset.nodes.length; i++) {
      n = dataset.nodes[i]
      if (n.Probability >= startThresh && n.Probability <= endThresh) {
        newNodes.push(n)
      }
      else {
        oldNodes.push(n)
      }
    }
    newLinks = dataset.links.filter(
      function(l) {
          for(let i = 0; i < oldNodes.length; i++){
              if (l.source.id == oldNodes[i].id || l.target.id == oldNodes[i].id) {
                  return false;
              }
          }
          return true;
      }
  )
  linkElements = g.append('g')
  .attr("class", "links")
  .selectAll("line")
  .data(newLinks)
  .enter().append("line")
  .style("stroke", "#ADA9A8")
  .style("stroke-width", function(d) { return (d.weight); });

//const nodeElements = svg.append('g')
/*nodeElements = svg.append('g')
.attr('class', 'nodes')
.selectAll('circle')
.data(allNodes)
.enter()
.append('circle')
.attr('r', function(d){return nodescale(d.Probability)})
.attr('fill', function(d){return myColor(d.Class) })
.classed('node', true)
.classed("fixed", d => d.fx !== undefined);*/

nodeElements = g.append('g')
.attr('class', 'nodes')
.selectAll('circle')
.data(newNodes)
.enter()
.append('g')
.attr('class', 'nodeHolder');

nodeElements
.append('circle')
.attr('r', function(d){return nodescale(d.Probability)})
.attr('fill', function(d){return myColor(d.Class) })
.classed('node', true)
.classed("fixed", d => d.fx !== undefined);

zoom_handler = d3.zoom().on('zoom', onZoomAction);
zoom_handler(svg);

nodeElements.append("text")
.attr("text-anchor", "middle")
.text(function(d) { return d.Symbol; })
.attr('alignment-baseline', 'middle')
.style("font-size", "50%");

nodeElements.call(d3.drag()
.on("start", onDragStarted)
.on("drag", onDrag)
.on("end", onDragEnded))
.on('click', onClick);
    simulation.alpha(1).restart();
  }

  d3.select("#download_as_png")
    .on('click', function(){
        console.log('In download chart');
        // Get the d3js SVG element and save using saveSvgAsPng.js
        saveSvgAsPng(document.getElementsByTagName("svg")[0], "plot.png", {scale: 2, backgroundColor: "#FFFFFF"});
    });

    d3.select("#download_as_svg")
    .on('click', function(){
        console.log('In download chart');
        // Get the d3js SVG element and save using saveSvgAsPng.js
        saveSvg(document.getElementsByTagName("svg")[0], "plot.svg", {scale: 2, backgroundColor: "#FFFFFF"});
    });
});