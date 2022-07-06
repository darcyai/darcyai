# Create a callback function for handling the input that is about to pass to the People Perceptor
def people_input_callback(input_data, pom, config):
    # Just take the frame from the incoming Input Stream and send it onward - no need to modify the frame
    frame = input_data.data.copy()
    return frame

# Create a callback function for handling the "New Person" event from the People Perceptor
# Just print the person ID to the console
def new_person_callback(person_id):
    print("New person: {}".format(person_id))

# Instantiate a People Perceptor
people_ai = PeoplePerceptor()

# Subscribe to the "New Person" event from the People Perceptor and use our callback from above as the handler
people_ai.on("new_person_entered_scene", new_person_callback)