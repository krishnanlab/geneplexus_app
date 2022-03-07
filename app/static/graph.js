//////////// OPTIONS
var graph_node_size = 10;
var graph_text_size = '75%'
var graph_initial_zoom = 1;
var graph_aspect_ratio = 2;
var graph_initial_node_count = 20;
var graph_initiaL_min_edge_weight = 1;
var graph_initial_node_prob = 0.0;
var graph_node_colors = ["#648FFF","#97B4FF","#FFB000"];


function clamp(n, min, max) {
  return Math.min(Math.max(n, min), max);
}

allNodes = dataset.nodes.sort((a, b) => (a.Probability - b.Probability));

maxNodesValue = dataset.nodes.length;

$( document ).ready(function() {
  // r = 0;
  $('body').on('click', '#graph_tab', function() {
    
    var width = $('.result_container').width() * (8/12);
    var height = width / graph_aspect_ratio;
    // r = -parseInt(Math.min(width, height) / 4)
    svg
      .attr('width', width)
      .attr('height', height);
  });
  var api_endpoint = 'https://mygene.info/v3/query/q=entrezgene:'
  var width = $('.result_container').width() * (8/12);
  var height = width / graph_aspect_ratio;
  selectedNode = null;
  selectedEdges = [];

  const svg = d3.select('svg');
  const g = svg.append('g');
  const data = ['P','U','N'];
  const myColor = d3.scaleOrdinal().domain(data)
       .range(graph_node_colors);

  var curNodes = allNodes.slice(0, graph_initial_node_count);
  var curLinks = getLinksByNodes(curNodes, graph_initiaL_min_edge_weight);
  graph_initial_node_prob = curNodes[curNodes.length-1].Probability.toPrecision(2);

  initial_slider_values = {'node_prob_slider': graph_initial_node_prob, 'node_count_slider': graph_initial_node_count, 'edge_weight_slider': graph_initiaL_min_edge_weight}
     

  var sliderTooltip = function(event, ui) {
    var curValue = ui.value  || initial_slider_values[$(event.target).attr('id')]; // current value (when sliding) or initial value (at start)

    var tooltip = '<div class="tooltip"><div class="tooltip-inner">' + curValue + '</div><div class="tooltip-arrow"></div></div>';

    $(this).find('.ui-slider-handle').html(tooltip); //attach tooltip to the slider handle
  }

  
  $('#node_prob_slider').slider({
    min: 0,
    max: 1.00,
    step: 0.01,
    value: initial_slider_values['node_prob_slider'],
    slide: function (event, ui) {
      clamped = clamp(ui.value, 0.0, 1.0)
      $(this).slider('option', 'value', clamped);
      modifyByNodeProbability(clamped);
      updateSliderTooltips();
    },
    create: sliderTooltip

  });

  $('#node_count_slider').slider({
    min: 0,
    max: dataset.nodes.length,
    step: 1,
    value: initial_slider_values['node_count_slider'],
    slide: function (event, ui) {
      clamped = clamp(ui.value, 0, dataset.nodes.length);
      $(this).slider('option', 'value', clamped);
      modifyByNodeCount(clamped);
      updateSliderTooltips();
    },
    create: sliderTooltip
  });

  $('#edge_weight_slider').slider({
    min: 0,
    max: 1.00,
    step: 0.01,
    value: initial_slider_values['edge_weight_slider'],
    slide: function (event, ui) {
      clamped = clamp(ui.value, 0.0, 1.0)
      $(this).slider('option', 'value', clamped);
      nodeCount = $('#node_count_slider').slider('option', 'value');
      modifyByEdgeWeight(nodeCount, clamped);
      updateSliderTooltips();
    },
    create: sliderTooltip

  });

  const forceProperties = {
    charge: {
      strength: -75,
    },
    collide: {
      strength: 0.3,
      radius: graph_node_size *2
    },

  }



  const simulation = d3.forceSimulation()
    .force('link', d3.forceLink())
    .force('charge', d3.forceManyBody()) 
    .force('collide', d3.forceCollide())
    //.force('center', d3.forceCenter(width / 2, height / 2))
    .force("forceX", d3.forceX(width/2).strength(.05) )
    .force("forceY", d3.forceY(height/2).strength(.05) );

  simulation.nodes(dataset.nodes).on('tick', onTick);

  simulation.force('charge').strength(forceProperties.charge.strength);
  simulation.force('collide').strength(forceProperties.collide.strength).radius(forceProperties.collide.radius);
  simulation.force('link').id(function(d) {return d.id}).links(dataset.links);
  
  // create a new graph from initial data and parameters 
  regenerateGraph(curNodes, curLinks) 

  // NOTE this is commented out here in favor of identical code in the 'regenerateGraph() function
  
  // var linkElements = g.append('g')
  //         .attr("class", "links")
  //         .selectAll("line")
  //         .data(curLinks)
  //         //.data(dataset.links)
  //         .enter().append("line")
  //         .style("stroke", "#ADA9A8")
  //         .style('stroke-width', '2')
  //         //.style("stroke-width", function(d) { return (d.weight); });

  // var nodeElements = g.append('g')
  //   .attr('class', 'nodes')
  //   .attr('r', graph_node_size)
  //   .selectAll('circle')
  //   .data(curNodes)
  //   .enter()
  //   .append('g')
  //   .attr('class', 'nodeHolder');

  // nodeElements
  //   .append('circle')
  //   .attr('r', graph_node_size)
  //   //.attr('r', function(d){return nodescale(d.Probability)})
  //   .attr('fill', function(d){return myColor(d.Class) })
  //   .classed('node', true)
  //   .classed("fixed", d => d.fx !== undefined);
  

  
  //     //svg.call(d3.zoom().on('zoom', onZoomAction)).on("dblclick.zoom", null);
  // zoom_handler = d3.zoom().on('zoom', onZoomAction);
  // zoom_handler(svg);
  // //zoom_handler(svg).on("dblclick.zoom", null);
  // svg.call(zoom_handler.transform, d3.zoomIdentity.scale(0.8));
  // svg.on("dblclick.zoom", null);

  // nodeElements.append("text")
  // .attr("text-anchor", "middle")
  // .classed("nodelabel")
  // .text(function(d) { return d.Symbol; })
  // .style('transform', 'translate(0px, -15px)')
  // .style("font-size", "50%");
  
  // nodeElements.call(d3.drag()
  // .on("start", onDragStarted)
  // .on("drag", onDrag)
  // .on("end", onDragEnded))
  // .on('click', onClick)
  // .on('dblclick', onDblClick);

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
    toScale = d3.event.transform
    g.attr("transform", toScale)
  }

  function onDragStarted(d) {
    d3.select(this).classed("fixed", true);
  }

  function onDrag(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
    // simulation.alpha(0.1).restart();
  }

  function onDragEnded(d) {
    simulation.alpha(1).restart();
  }

  function onClick(d) {
    theCircle = d3.select(this).select('circle');
    if (selectedNode != null) {
      selectedNode.style('stroke', 'transparent');
    }
    setSidebarInformation(d);
    theCircle.style('stroke', 'red');
    selectedNode = theCircle;
  }

  function onDblClick(d) {
    delete d.fx;
    delete d.fy;
    theCircle.classed("fixed", false);
  }

  function setSidebarInformation(d) {
    $('#static_id').text(d.id)
      .attr('href', 'https://www.ncbi.nlm.nih.gov/gene/' + d.id)
      .attr('target', '_blank');
    $('#static_class').text(d['Training-Label']);
    $('#static_known').text(d['Known/Novel'])
    $('#static_name').text(d.Name);
    $('#static_prob').text(d.Probability.toPrecision(2));
    $('#static_rank').text(d.Rank);
    $('#static_symbol').text(d.Symbol);
    $('#static_site').text('Click here');
    $.ajax({
      method: 'GET',
      url: 'https://mygene.info/v3/gene/' + d.id,
      success: function(result, status, xhr) {
        if (typeof result.type_of_gene != 'undefined') {
          $('#static_genetype').text(result.type_of_gene);
        }
        else {
          $('#static_genetype').text('');
        }
        if (typeof result.uniprot != 'undefined' && 'Swiss-Prot' in result.uniprot) {
          $('#static_swissprot').text(result.uniprot['Swiss-Prot']);
        }
        else {
          $('#static_swissprot').text('');
        }
      },
      complete: function(xhr, status) {

      }
    });
  }

  function updateSliderTooltips() {
    edgeWeight = $('#edge_weight_slider').slider('value');
    nodeCount = $('#node_count_slider').slider('value');
    nodeProb = $('#node_prob_slider').slider('value');
    $('#edge_weight_slider').find('div.tooltip-inner').text(edgeWeight);
    $('#node_count_slider').find('div.tooltip-inner').text(nodeCount);
    $('#node_prob_slider').find('div.tooltip-inner').text(nodeProb);
  }

  function modifyByNodeCount(nodeCount) {
    var newNodes = [];
    console.log(nodeCount);
    var minProb = 0.0;
    if (nodeCount > 0) {
      newNodes = allNodes.slice(0, nodeCount);
      minProb = newNodes[newNodes.length - 1].Probability;
    }
    threshold = $('#edge_weight_slider').slider('option', 'value');
    newLinks = getLinksByNodes(newNodes, threshold);
    if (minProb < $('#node_prob_slider').slider('option', 'value')) {
      $('#node_prob_slider').slider('option', 'value', minProb);
    }
    regenerateGraph(newNodes, newLinks);
  }

  function modifyByNodeProbability(nodeProbability) {
    newNodes = [];
    for (let i = 0; i < allNodes.length; i++) {
      n = allNodes[i]
      if (n.Probability >= nodeProbability) {
        newNodes.push(n)
      }
    }
    threshold = $('#edge_weight_slider').slider('option', 'value');
    newLinks = getLinksByNodes(newNodes, threshold);
    $('#node_count_slider').slider('option', 'value', newNodes.length);
    regenerateGraph(newNodes, newLinks);
  }

  function modifyByEdgeWeight(nodeCount, edgeWeight) {
    newNodes = allNodes.slice(0, nodeCount);
    newLinks = getLinksByNodes(newNodes, edgeWeight);
    regenerateGraph(newNodes, newLinks);
  }

  function regenerateGraph(nodes, links) {
    currentTransform = g.attr('transform');
    d3.selectAll('g.nodes').remove();
    d3.selectAll('g.links').remove();

    linkElements = g.append('g')
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .enter().append("line")
      .style("stroke", "#ADA9A8");

    nodeElements = g.append('g')
    .attr('class', 'nodes')
    .selectAll('circle')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'nodeHolder');

    nodeElements
    .append('circle')
    .attr('r', graph_node_size)
    .attr('fill', function(d){return myColor(d["Training-Label"]) })  // previously was Class, requires [] since column has a hypen in it
    .classed('node', true)
    .classed("fixed", d => d.fx !== undefined);

    zoom_handler = d3.zoom().on('zoom', onZoomAction);
    zoom_handler(svg);
    g.attr('transform', currentTransform);
    //svg.call(zoom_handler.transform, d3.zoomIdentity.scale(0.8));
    svg.on("dblclick.zoom", null);

    nodeElements.append("text")
    .attr("text-anchor", "middle")
    .text(function(d) { return d.Symbol; })
    .style('transform', 'translate(0px, -15px)')
    .style("font-size", graph_text_size);

    nodeElements.call(d3.drag()
    .on("start", onDragStarted)
    .on("drag", onDrag)
    .on("end", onDragEnded))
    .on('click', onClick)
    .on('dblclick', onDblClick);

    simulation.alpha(1).restart();
  }

  function getLinksByNodes(nodeList, threshold = 0) {
    var nodeIds = [];
    for (let i = 0; i < nodeList.length; i++) {
      nodeIds.push(nodeList[i].id);
    }
    // console.log(nodeIds);
    return dataset.links.filter(
      function(l) {
        return nodeIds.indexOf(l.source.id) > -1 && nodeIds.indexOf(l.target.id) > -1 && l.weight > threshold;
      }
    )
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