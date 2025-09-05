# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import networkx as nx
import streamlit as st
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
import html

st.title("🕸️ Knowledge Graph Explorer")
    
def graphml_to_elements(graphml_path: str) -> dict:
    """
    Convert a GraphML file to the elements format required by st_link_analysis.
    """
    G = nx.read_graphml(graphml_path)
    elements = {
        "nodes": [],
        "edges": []
    }

    # Add nodes with relevant attributes
    for node in G.nodes(data=True):
        node_id = str(node[0])

        # Strip quotes and decode XML entities
        description = html.unescape(node[1].get('description', '').strip('"'))
        type = html.unescape(node[1].get('entity_type', '').strip('"'))
        
        # Split description on <SEP> if needed
        descriptions = description.split('<SEP>') if description else []
        # Use first description or empty string if none
        main_description = descriptions[0] if descriptions else ''
        
        elements["nodes"].append({
            "data": {
                "id": node_id,
                "label": node_id.strip('"'),
                "description": main_description,
                "type": type,
                "all_descriptions": descriptions  # Optional: keep all descriptions
            }
        })

    # Add edges with relevant attributes
    for edge in G.edges(data=True):
        edge_id = f"{edge[0]}_{edge[1]}"
        # Get relationship description and type from attributes
        relationship = edge[2].get('description', '').strip('"')  # Description
        rel_type = edge[2].get('keywords', '').strip('"')     # Type/keywords as relationship type
        strength = edge[2].get('weight', 1.0)               # Relationship strength
        
        elements["edges"].append({
            "data": {
                "id": edge_id,
                "source": str(edge[0]),
                "target": str(edge[1]),
                "label": rel_type,
                "relationship": rel_type,  # Use keywords/type as the label
                "description": relationship,  # Keep full description
                "strength": strength,
            }
        })

    return elements

def main():

    # Scan ./data for persona folders
    data_dir = "./data"
    if not os.path.exists(data_dir):
        st.error(f"The data directory `{data_dir}` does not exist.")
        return

    persona_folders = [
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d))
    ]

    if not persona_folders:
        st.warning("No persona folders found in the data directory.")
        return

    # Dropdown to pick a persona folder
    persona_choice = st.selectbox("Select a Persona", persona_folders)

    # Build path to .graphml (assuming the file is named 'graph_chunk_entity_relation.graphml')
    graphml_filename = "graph_chunk_entity_relation.graphml"
    graphml_path = os.path.join(data_dir, persona_choice, graphml_filename)

    # Button to display the graph
    if (st.button("Display Graph")):
        if os.path.exists(graphml_path):
            try:
                elements = graphml_to_elements(graphml_path)

                #initialise empty
                processed_elements = {
                    "nodes": [],
                    "edges": []
                }

                # Define node styles once
                node_styles = [
                    NodeStyle(label="PERSON", color="#FF7F3E", caption="name", icon="person"),
                    NodeStyle(label="POST", color="#2A629A", caption="content", icon="description"),
                    NodeStyle(label="EVENT", color="#FF3E3E", caption="name", icon="event"),
                    NodeStyle(label="ORGANIZATION", color="#3EFF3E", caption="name", icon="organization"),
                    NodeStyle(label="CONCEPT", color="#3E3EFF", caption="name", icon="concept"),
                    NodeStyle(label="GEO", color="#FF3E7F", caption="name", icon="location"),
                    NodeStyle(label="DEFAULT", color="#CCCCCC", caption="label", icon="default")
                ]

                # Configure layout
                layout = {
                    "name": "cose",
                    "animate": "end",
                    "nodeDimensionsIncludeLabels": False
                }

                # Update node data to include label field
                for node in elements["nodes"]:
                    entity_type = node["data"].get("type", "").strip('"')
                    if entity_type:
                        node["data"]["label"] = entity_type

                    processed_elements["nodes"].append(node)

                # Create a set of unique relationships from the edges
                unique_relationships = set()
                for edge in elements["edges"]:
                    relationship = ', '.join(edge["data"].get("label", "").strip('"').split('"<SEP>"'))
                    print("original relationship:", edge["data"].get("label", ""))
                    print("after editing relationship:", relationship)
                    if relationship:
                        unique_relationships.add(relationship)
                        edge["data"]["label"] = relationship

                    processed_elements["edges"].append(edge)

                # Generate dynamic edge styles based on unique relationships
                edge_styles = []
                for rel in unique_relationships:
                    print("Added edge style for relationship:", rel)
                    edge_styles.append(EdgeStyle(rel, caption="label", labeled=True, directed=True))
                # Add default style for any undefined relationships
                edge_styles.append(EdgeStyle("DEFAULT", labeled=True, directed=True))

                # Render the graph using st_link_analysis
                st.markdown(f"### Knowledge Graph for **{persona_choice}**")
                st_link_analysis(
                    processed_elements, 
                    layout=layout, 
                    node_styles=node_styles, 
                    edge_styles=edge_styles,
                    key=f"graph_{persona_choice}"
                )

            except Exception as e:
                st.error(f"An error occurred while processing the graph: {e}")
        else:
            st.error(f"No `.graphml` file found for the selected persona: `{persona_choice}`. Try running a query on chat page with the persona first to begin knowledge indexing!")

main()
