#!/bin/bash
# Fix Path Inconsistencies
# Replace old /opt/coinjecture-consensus paths with /opt/coinjecture

echo "🔧 Fixing path inconsistencies..."

# Files to update (excluding CHANGELOG.md and backup files)
FILES_TO_UPDATE=(
    "scripts/delete_old_code.sh"
    "scripts/delete_old_databases.sh" 
    "scripts/complete_system_reset.sh"
    "scripts/update_consensus_services.py"
    "scripts/fix_p2p_network_connectivity.py"
    "scripts/diagnose_consensus_processing.sh"
    "scripts/deploy_p2p_fix_remote.py"
    "scripts/deploy_database_fix_to_droplet.sh"
    "scripts/complete_droplet_fix.sh"
    "scripts/complete_power_cycle_deployment.sh"
    "scripts/deploy_integrated_api_to_droplet.sh"
    "scripts/deploy_integrated_api.sh"
    "src/api/cache_manager.py"
    "scripts/migrate_rewards_dynamic_tokenomics.py"
    "scripts/deployment/deploy_api_fix.sh"
    "scripts/deployment/deploy_mobile_fix.sh"
    "scripts/setup/consolidate_data_sources.sh"
    "scripts/deploy_memory_efficient_fix.sh"
    "scripts/memory_efficient_consensus_fix.py"
    "scripts/deploy_consensus_fix.sh"
    "scripts/coinjecture-consensus-monitor.service"
    "src/api/health_monitor_api.py"
    "scripts/fix_consensus_database_path.sh"
    "scripts/deploy_p2p_consensus.py"
)

# Update each file
for file in "${FILES_TO_UPDATE[@]}"; do
    if [ -f "$file" ]; then
        echo "📝 Updating $file..."
        # Replace /opt/coinjecture-consensus with /opt/coinjecture
        sed -i.bak 's|/opt/coinjecture-consensus|/opt/coinjecture|g' "$file"
        # Remove backup file
        rm -f "$file.bak"
        echo "✅ Updated $file"
    else
        echo "⚠️  File not found: $file"
    fi
done

echo "✅ Path inconsistencies fixed!"
echo "📋 Summary:"
echo "   - Replaced /opt/coinjecture-consensus with /opt/coinjecture"
echo "   - Updated $(echo "${FILES_TO_UPDATE[@]}" | wc -w) files"
echo "   - All paths now consistent with architecture"
