import json

def restructure_json(input_file, output_file):
    # Read the input JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Create the new structure
    new_structure = []

    for product in data:
        new_product = {
            "text": product["Product Title"],
            "Reviewer_Details": {}
        }

        # Process reviewer details
        for review_key, review_data in product["Reviewer Details"].items():
            new_review_key = f"customer_review-{review_key}"
            new_product["Reviewer_Details"][new_review_key] = {
                "review": review_data["review_content"]
            }

        new_structure.append(new_product)

    # Write the new structure to the output file
    with open(output_file, 'w') as f:
        json.dump(new_structure, f, indent=2)

    print(f"Restructured JSON has been written to {output_file}")

# Use the function
input_file = "Ulta-Products-Reviews-Cleanser.json"
output_file = "cleaned_cleanser_ulta_reviews.json"
restructure_json(input_file, output_file)