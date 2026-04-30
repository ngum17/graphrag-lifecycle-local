FROM neo4j:5.22.0

ENV NEO4JLABS_PLUGINS '[ "apoc" ]'
ENV NEO4J_dbms_security_procedures_unrestricted apoc.*

# Stáhnout APOC plugin
RUN wget -O /var/lib/neo4j/plugins/apoc-5.22.0-core.jar \
    https://github.com/neo4j/apoc/releases/download/5.22.0/apoc-5.22.0-core.jar || \
    echo "⚠️ APOC stažení selhalo, ale Neo4j běží bez něj"

EXPOSE 7474 7687
