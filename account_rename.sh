#!/bin/bash

function update_account_name() {
    response=$(aws organizations list-accounts \
        --output text \
        --query "Accounts[].[Id, Name]")

    echo "$response" | while read -r id name; do
        echo "Account ID: $id, Name: $name"

        # Añadir filtro para cambio de nombre, selecciona unicamente las cuentas que ternminan con " SB"
        if [[ $name == *SB ]]; then
            new_name=${name%" SB"}
            echo "Changing '$name' to '$new_name'"
            aws account put-account-name \
                --account-id "$id" \
                --account-name "$new_name"
            continue
        else
            echo "Skipping '$name'"
        fi
    done
}

update_account_name