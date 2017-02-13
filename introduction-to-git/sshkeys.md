# Gestion des clé d'identification

Ouvrir Git-bash ou le terminal

Pour générer une paire de clé de chiffrement publique/privée

	ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

Lorsque la console vous demande: "Enter a file in which to save the key," pressez Enter. 
Cela utilise les valeurs par défaut.

	Enter a file in which to save the key (/Users/you/.ssh/id_rsa): [Press enter]

L'invite suivante vous propose de protéger votre clé par un mot de passe:

	Enter passphrase (empty for no passphrase): [Type a passphrase]
	Enter same passphrase again: [Type passphrase again]

Vos clés publique/privée sont créées. Il suffit copier le contenu de votre clé publique 
sur le serveur distant pour activer le cryptage de vos communications futures avec celui-ci.